import asyncio
import csv
import os
import pytest
import subprocess

from datetime import datetime, timezone
from collections import defaultdict
from src.analyzeMFT.mft_analyzer import MftAnalyzer
from src.analyzeMFT.constants import CSV_HEADER

@pytest.fixture(scope="module")
def synthetic_mft():
    subprocess.run(["python", "generateMFT.py", "--output", "synthetic.mft", "--size", "1000"], check=True)
    yield "synthetic.mft"
    os.remove("synthetic.mft")

@pytest.fixture(scope="module")
def analyzed_output(synthetic_mft):
    output_file = "analyzed_output.csv"
    asyncio.run(analyze_synthetic_mft(synthetic_mft, output_file))
    yield output_file
    os.remove(output_file)

async def analyze_synthetic_mft(mft_file, output_file):
    analyzer = MftAnalyzer(mft_file, output_file, debug=False, compute_hashes=True, export_format="csv")
    await analyzer.analyze()

def test_synthetic_mft_analysis(analyzed_output):
    with open(analyzed_output, 'r', newline='') as f:
        csv_reader = csv.DictReader(f)
        records = list(csv_reader)

    # Check if we have the expected number of records
    assert len(records) == 1000, f"Expected 1000 records, but got {len(records)}"

    # Initialize counters and collections for various checks
    file_types = defaultdict(int)
    record_statuses = defaultdict(int)
    unique_parent_records = set()
    filename_extensions = defaultdict(int)
    time_ranges = {
        'si_crtime': {'min': datetime.max, 'max': datetime.min},
        'fn_crtime': {'min': datetime.max, 'max': datetime.min},
    }

    for record in records:
        # Check record status and type
        record_statuses[record['Record Status']] += 1
        file_types[record['File Type']] += 1

        # Check parent record numbers
        unique_parent_records.add(record['Parent Record Number'])

        # Check filename and extensions
        if record['Filename']:
            ext = os.path.splitext(record['Filename'])[1].lower()
            filename_extensions[ext] += 1

        # Check time ranges
        for time_field in ['SI Creation Time', 'FN Creation Time']:
            if record[time_field] and record[time_field] != "Not defined":
                dt = datetime.fromisoformat(record[time_field].rstrip('Z')).replace(tzinfo=timezone.utc)
                field_key = 'si_crtime' if time_field.startswith('SI') else 'fn_crtime'
                time_ranges[field_key]['min'] = min(time_ranges[field_key]['min'], dt)
                time_ranges[field_key]['max'] = max(time_ranges[field_key]['max'], dt)

        # Check for presence of specific attributes
        assert record['Has Standard Information'] in ['True', 'False']
        assert record['Has File Name'] in ['True', 'False']

        # If it's a file, it should have a Data attribute
        if record['File Type'] == 'File':
            assert record['Has Data'] == 'True', f"File record {record['Record Number']} missing Data attribute"

        # Check for valid sequence numbers
        assert record['Sequence Number'].isdigit(), f"Invalid Sequence Number: {record['Sequence Number']}"

    # Perform assertions based on collected data
    assert record_statuses['Valid'] == 1000, f"Expected all records to be Valid, but got {record_statuses['Valid']}"
    assert record_statuses['In Use'] > 0, "Expected some records to be In Use"
    assert file_types['File'] > 0, "Expected some File records"
    assert file_types['Directory'] > 0, "Expected some Directory records"
    assert len(unique_parent_records) > 1, "Expected multiple parent records"

    # Check for common file extensions
    assert filename_extensions['.txt'] > 0, "Expected some .txt files"
    assert filename_extensions['.exe'] > 0, "Expected some .exe files"
    assert filename_extensions['.dll'] > 0, "Expected some .dll files"

    # Check time ranges
    for time_field, range_data in time_ranges.items():
        assert range_data['min'] < range_data['max'], f"Invalid time range for {time_field}"
        assert (range_data['max'] - range_data['min']).days < 365 * 10, f"Time range for {time_field} exceeds 10 years"

    # Check for specific system files or directories
    assert any(record['Filename'] == 'MFT' for record in records), "MFT file not found"
    assert any(record['Filename'] == 'Windows' and record['File Type'] == 'Directory' for record in records), "Windows directory not found"

    # Add more specific checks based on what you know about the synthetic data generated
    # For example, if generateMFT.py creates specific file structures or patterns, check for those here

    print("Synthetic MFT analysis test passed successfully!")

def test_synthetic_mft_statistics(synthetic_mft):
    analyzer = MftAnalyzer(synthetic_mft, "temp_output.csv", debug=False, compute_hashes=True, export_format="csv")
    asyncio.run(analyzer.analyze())

    # Check if the statistics are as expected
    assert analyzer.stats['total_records'] == 1000
    assert analyzer.stats['active_records'] > 0
    assert analyzer.stats['directories'] > 0
    assert analyzer.stats['files'] > 0
    assert len(analyzer.stats['unique_md5']) > 0
    assert len(analyzer.stats['unique_sha256']) > 0
    assert len(analyzer.stats['unique_sha512']) > 0
    assert len(analyzer.stats['unique_crc32']) > 0

    os.remove("temp_output.csv")

def test_root_directory(analyzed_output):
    with open(analyzed_output, 'r', newline='') as f:
        csv_reader = csv.DictReader(f)
        root = next(record for record in csv_reader if record['Record Number'] == '5')
    
    assert root['File Type'] == 'Directory'
    assert root['Filename'] == '.'
    assert root['Parent Record Number'] == '5'

def test_file_sizes(analyzed_output):
    with open(analyzed_output, 'r', newline='') as f:
        csv_reader = csv.DictReader(f)
        file_sizes = [int(record['SI File Size']) for record in csv_reader if record['File Type'] == 'File' and record['SI File Size'].isdigit()]
    
    assert len(file_sizes) > 0, "No valid file sizes found"
    assert min(file_sizes) >= 0, "Found negative file size"
    assert max(file_sizes) < 1024 ** 4, "Found unreasonably large file size"

def test_attribute_consistency(analyzed_output):
    with open(analyzed_output, 'r', newline='') as f:
        csv_reader = csv.DictReader(f)
        for record in csv_reader:
            if record['File Type'] == 'Directory':
                assert record['Has Index Root'] == 'True', f"Directory {record['Record Number']} missing Index Root"
            if record['Has Object ID'] == 'True':
                assert record['Object ID'], f"Record {record['Record Number']} has Object ID attribute but no Object ID value"