import os
import logging
from mft_core import MFTAnalyzer
from mft_output import MFTOutputSession
from config import get_config
from error_handler import (
    setup_logging, error_handler, MFTAnalysisError, IOError,
    ParsingError, ConfigurationError, log_and_raise, handle_critical_error
)

@error_handler({
    OSError: IOError,
    ValueError: ConfigurationError,
    KeyError: ConfigurationError,
})
def main():
    try:
        config = get_config()
        setup_logging(config.log_level, getattr(config, 'log_file', None))

        file_size = os.path.getsize(config.input_file)
        logging.info(f"Input file size: {file_size} bytes")

        if file_size == 0:
            log_and_raise(IOError, "Input file is empty")

        analyzer = MFTAnalyzer(config)
        output_session = MFTOutputSession(config)

        with open(config.input_file, 'rb') as mft_file:
            analyzer.process_file(mft_file)

        if config.reconstruct_paths:
            logging.info("Reconstructing file paths...")
            analyzer.reconstruct_file_paths()

        if config.anomaly_detection:
            logging.info("Running anomaly detection...")
            anomalies = analyzer.detect_anomalies()
            for anomaly in anomalies:
                logging.warning(f"Anomaly detected: {anomaly}")

        logging.info("Writing output...")
        for record in analyzer.records.values():
            output_session.write_record(record)

        logging.info(f"Processed {len(analyzer.records)} records")

    except IOError as e:
        logging.error(f"IO Error: {e}")
        raise
    except (ConfigurationError, ParsingError) as e:
        logging.error(f"Configuration or Parsing Error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise MFTAnalysisError("An unexpected error occurred") from e
    finally:
        if 'output_session' in locals():
            output_session.close()

if __name__ == "__main__":
    try:
        main()
    except MFTAnalysisError as e:
        handle_critical_error(e)