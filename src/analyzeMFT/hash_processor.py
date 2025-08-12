import hashlib
import zlib
import multiprocessing as mp
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class HashResult:
    record_index: int
    md5: str
    sha256: str
    sha512: str
    crc32: str
    processing_time: float


def compute_hashes_for_record(data: Tuple[int, bytes]) -> HashResult:
    record_index, raw_record = data
    start_time = time.time()
    
    try:
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        sha512 = hashlib.sha512()
        md5.update(raw_record)
        sha256.update(raw_record)
        sha512.update(raw_record)
        md5_hash = md5.hexdigest()
        sha256_hash = sha256.hexdigest()
        sha512_hash = sha512.hexdigest()
        crc32_hash = format(zlib.crc32(raw_record) & 0xFFFFFFFF, '08x')
        
        processing_time = time.time() - start_time
        
        return HashResult(
            record_index=record_index,
            md5=md5_hash,
            sha256=sha256_hash,
            sha512=sha512_hash,
            crc32=crc32_hash,
            processing_time=processing_time
        )
    except Exception as e:
        logger = logging.getLogger('analyzeMFT.hash_processor')
        logger.warning(f"Error computing hashes for record {record_index}: {e}")
        
        processing_time = time.time() - start_time
        return HashResult(
            record_index=record_index,
            md5="",
            sha256="",
            sha512="",
            crc32="",
            processing_time=processing_time
        )


class HashProcessor:

    def __init__(self, num_processes: Optional[int] = None, logger: Optional[logging.Logger] = None):
        self.num_processes = num_processes or get_optimal_process_count()
        self.logger = logger or logging.getLogger('analyzeMFT.hash_processor')
        self.stats = {
            'total_records': 0,
            'total_processing_time': 0.0,
            'multiprocessing_overhead': 0.0,
            'average_time_per_record': 0.0,
            'processes_used': self.num_processes
        }
        
    def compute_hashes_single_threaded(self, raw_records: List[bytes]) -> List[HashResult]:
        if not raw_records:
            return []
            
        start_time = time.time()
        results = []
        
        for i, raw_record in enumerate(raw_records):
            try:
                result = compute_hashes_for_record((i, raw_record))
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Error processing record {i} in single-threaded mode: {e}")
                results.append(HashResult(
                    record_index=i,
                    md5="",
                    sha256="",
                    sha512="",
                    crc32="",
                    processing_time=0.0
                ))
            
        total_time = time.time() - start_time
        self.stats.update({
            'total_records': len(raw_records),
            'total_processing_time': total_time,
            'average_time_per_record': total_time / len(raw_records) if raw_records else 0,
            'processes_used': 1
        })
        
        self.logger.debug(f"Single-threaded hash computation: {len(raw_records)} records in {total_time:.3f}s")
        return results
        
    def compute_hashes_multiprocessed(self, raw_records: List[bytes]) -> List[HashResult]:
        
        if not raw_records:
            return []
            
        if len(raw_records) < 10:
            return self.compute_hashes_single_threaded(raw_records)
            
        start_time = time.time()
        indexed_records = [(i, record) for i, record in enumerate(raw_records)]
        
        results = [None] * len(raw_records) 
        
        try:
            with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
                mp_start = time.time()
                future_to_index = {
                    executor.submit(compute_hashes_for_record, data): data[0] 
                    for data in indexed_records
                }
                
                completed_count = 0
                for future in as_completed(future_to_index):
                    try:
                        result = future.result()
                        results[result.record_index] = result
                        completed_count += 1
                        
                        if len(raw_records) > 1000 and completed_count % 1000 == 0:
                            self.logger.debug(f"Processed {completed_count}/{len(raw_records)} records")
                            
                    except Exception as e:
                        record_index = future_to_index[future]
                        self.logger.warning(f"Error processing record {record_index} in multiprocessed mode: {e}")
                        results[record_index] = HashResult(
                            record_index=record_index,
                            md5="",
                            sha256="",
                            sha512="",
                            crc32="",
                            processing_time=0.0
                        )
                
                for i, result in enumerate(results):
                    if result is None:
                        self.logger.warning(f"Missing result for record {i}")
                        results[i] = HashResult(
                            record_index=i,
                            md5="",
                            sha256="",
                            sha512="",
                            crc32="",
                            processing_time=0.0
                        )
            
            mp_overhead = time.time() - mp_start
            total_time = time.time() - start_time
            
            self.stats.update({
                'total_records': len(raw_records),
                'total_processing_time': total_time,
                'multiprocessing_overhead': mp_overhead,
                'average_time_per_record': total_time / len(raw_records) if raw_records else 0,
                'processes_used': self.num_processes
            })
            
            self.logger.debug(f"Multiprocessed hash computation: {len(raw_records)} records in {total_time:.3f}s using {self.num_processes} processes")
            return results
            
        except Exception as e:
            self.logger.error(f"Multiprocessing failed, falling back to single-threaded: {e}")
            return self.compute_hashes_single_threaded(raw_records)
        
    def compute_hashes_adaptive(self, raw_records: List[bytes]) -> List[HashResult]:
        if not raw_records:
            return []
            
        mp_threshold = 50
        cpu_count = mp.cpu_count()
        
        use_multiprocessing = (
            len(raw_records) >= mp_threshold and
            cpu_count > 1 and
            len(raw_records) >= (cpu_count * 10)
        )
        
        if use_multiprocessing:
            self.logger.info(f"Using multiprocessing for {len(raw_records)} records with {self.num_processes} processes")
            return self.compute_hashes_multiprocessed(raw_records)
        else:
            self.logger.debug(f"Using single-threaded processing for {len(raw_records)} records")
            return self.compute_hashes_single_threaded(raw_records)
            
    def get_performance_stats(self) -> Dict[str, Any]:
        return self.stats.copy()
        
    def log_performance_summary(self) -> None:
        if self.stats['total_records'] == 0:
            return
            
        records_per_second = self.stats['total_records'] / self.stats['total_processing_time'] if self.stats['total_processing_time'] > 0 else 0
        avg_time_ms = self.stats['average_time_per_record'] * 1000
        
        self.logger.info("Hash computation performance:")
        self.logger.info(f"  Records processed: {self.stats['total_records']}")
        self.logger.info(f"  Total time: {self.stats['total_processing_time']:.3f}s")
        self.logger.info(f"  Records/second: {records_per_second:.1f}")
        self.logger.info(f"  Average time per record: {avg_time_ms:.2f}ms")
        self.logger.info(f"  Processes used: {self.stats['processes_used']}")
        
        if self.stats['processes_used'] > 1 and self.stats['total_processing_time'] > 0:
            efficiency = (self.stats['total_processing_time'] - self.stats['multiprocessing_overhead']) / self.stats['total_processing_time'] * 100
            self.logger.info(f"  Multiprocessing efficiency: {efficiency:.1f}%")


def get_optimal_process_count() -> int:
    cpu_count = mp.cpu_count()

    if cpu_count <= 2:
        return cpu_count
    elif cpu_count <= 4:
        return cpu_count
    elif cpu_count <= 8:
        return min(cpu_count, 6)
    else:
        return min(cpu_count - 2, 8)


def benchmark_hash_methods(raw_records: List[bytes], logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    if not raw_records:
        return {}
        
    logger = logger or logging.getLogger('analyzeMFT.hash_benchmark')
    
    processor_st = HashProcessor(num_processes=1, logger=logger)
    start_st = time.time()
    results_st = processor_st.compute_hashes_single_threaded(raw_records)
    time_st = time.time() - start_st
    
    processor_mp = HashProcessor(logger=logger)
    start_mp = time.time()
    results_mp = processor_mp.compute_hashes_multiprocessed(raw_records)
    time_mp = time.time() - start_mp
    
    verification_passed = True
    if len(results_st) == len(results_mp):
        for i, (st_result, mp_result) in enumerate(zip(results_st, results_mp)):
            if (st_result.md5 != mp_result.md5 or 
                st_result.sha256 != mp_result.sha256 or
                st_result.sha512 != mp_result.sha512 or
                st_result.crc32 != mp_result.crc32):
                verification_passed = False
                logger.error(f"Hash mismatch at record {i}: "
                           f"ST({st_result.md5[:8]}...) vs MP({mp_result.md5[:8]}...)")
                break
    else:
        verification_passed = False
        logger.error("Result count mismatch between single-threaded and multiprocessed")
        
    speedup = time_st / time_mp if time_mp > 0 else 0
    efficiency = (speedup / processor_mp.num_processes * 100) if processor_mp.num_processes > 0 else 0
    recommended_method = 'multiprocessing' if speedup > 1.2 else 'single_threaded'
    
    benchmark_results = {
        'records_tested': len(raw_records),
        'single_threaded_time': time_st,
        'multiprocessed_time': time_mp,
        'speedup_factor': speedup,
        'efficiency_percent': efficiency,
        'processes_used': processor_mp.num_processes,
        'verification_passed': verification_passed,
        'recommended_method': recommended_method
    }
    
    logger.info("Hash computation benchmark results:")
    logger.info(f"  Records: {benchmark_results['records_tested']}")
    logger.info(f"  Single-threaded: {time_st:.3f}s")
    logger.info(f"  Multiprocessed: {time_mp:.3f}s")
    logger.info(f"  Speedup: {speedup:.2f}x")
    logger.info(f"  Efficiency: {efficiency:.1f}%")
    logger.info(f"  Verification: {'PASSED' if verification_passed else 'FAILED'}")
    logger.info(f"  Recommended: {benchmark_results['recommended_method']}")
    
    return benchmark_results