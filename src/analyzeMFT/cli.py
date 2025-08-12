import asyncio
import logging
import argparse
import os
from pathlib import Path
import sys
from .mft_analyzer import MftAnalyzer
from .constants import VERSION
from .config import ConfigManager, find_config_file
from .test_generator import create_test_mft
from .validators import (
    validate_paths_secure, validate_numeric_bounds, validate_export_format,
    validate_config_schema, ValidationError, MFTValidationError, 
    PathValidationError, NumericValidationError, ConfigValidationError
)

def setup_logging(verbosity_level, debug_level):
    """Configure logging based on verbosity and debug levels."""
    if debug_level > 0:
        log_level = logging.DEBUG
    elif verbosity_level > 0:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze MFT (Master File Table) files from NTFS filesystems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -f mft.raw -o results.csv --csv
  %(prog)s -f mft.raw -o timeline.body --body
  %(prog)s --generate-test-mft test.mft --test-records 10000
        """
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

    # Required arguments
    parser.add_argument("-f", "--file", dest="filename",
                        help="MFT file to analyze", metavar="MFT_FILE")
    parser.add_argument("-o", "--output", dest="output_file",
                        help="Output file (use '-' for stdout)", metavar="OUTPUT_FILE")

    # Export format group (mutually exclusive)
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument("--csv", action="store_const", const="csv", dest="export_format",
                              help="Export as CSV (default)")
    export_group.add_argument("--json", action="store_const", const="json", dest="export_format",
                              help="Export as JSON")
    export_group.add_argument("--xml", action="store_const", const="xml", dest="export_format",
                              help="Export as XML")
    export_group.add_argument("--excel", action="store_const", const="excel", dest="export_format",
                              help="Export as Excel")
    export_group.add_argument("--body", action="store_const", const="body", dest="export_format",
                              help="Export as body file (for mactime)")
    export_group.add_argument("--timeline", action="store_const", const="timeline", dest="export_format",
                              help="Export as TSK timeline")
    export_group.add_argument("--l2t", action="store_const", const="l2t", dest="export_format",
                              help="Export as log2timeline CSV")
    export_group.add_argument("--sqlite", action="store_const", const="sqlite", dest="export_format",
                              help="Export as SQLite database")
    export_group.add_argument("--tsk", action="store_const", const="tsk", dest="export_format",
                              help="Export as TSK bodyfile format")

    # Verbosity options
    parser.add_argument("--verbose", "-V", action="count", dest="verbosity",
                        help="Increase output verbosity (can be used multiple times)", default=0)
    parser.add_argument("--debug", "-D", action="count", dest="debug",
                        help="Increase debug output (can be used multiple times)", default=0)

    # Performance options
    parser.add_argument("--chunk-size", dest="chunk_size", type=int, default=1000,
                        help="Number of records to process in each chunk (default: 1000)")
    parser.add_argument("--hash", action="store_true", dest="compute_hashes",
                        help="Compute hashes (MD5, SHA256, SHA512, CRC32)", default=False)
    parser.add_argument("--no-multiprocessing-hashes", action="store_false", dest="multiprocessing_hashes",
                        help="Disable multiprocessing for hash computation", default=True)
    parser.add_argument("--hash-processes", dest="hash_processes", type=int,
                        help="Number of processes for hash computation (default: auto-detect)")

    # Configuration options
    parser.add_argument("-c", "--config", dest="config_file", metavar="CONFIG_FILE",
                        help="Load configuration from JSON/YAML file")
    parser.add_argument("--profile", dest="profile_name", metavar="PROFILE_NAME",
                        help="Use predefined analysis profile (default, quick, forensic, performance)")
    parser.add_argument("--list-profiles", action="store_true", dest="list_profiles",
                        help="List available analysis profiles and exit")
    parser.add_argument("--create-config", dest="create_config", metavar="CONFIG_FILE",
                        help="Create a sample configuration file and exit")

    # Test options
    parser.add_argument("--test-mode", action="store_true", dest="test_mode",
                        help="Generate test MFT file and run analysis")
    parser.add_argument("--generate-test-mft", dest="generate_test_mft", metavar="TEST_MFT_FILE",
                        help="Generate a test MFT file and exit")
    parser.add_argument("--test-records", dest="test_records", type=int, default=1000,
                        help="Number of records in test MFT (default: 1000)")
    parser.add_argument("--test-type", dest="test_type", choices=["normal", "anomaly"],
                        default="normal", help="Type of test MFT to generate (normal, anomaly)")

    return parser

def handle_list_profiles(config_manager):
    """Handle the --list-profiles option."""
    profiles = config_manager.list_profiles()
    print("\nAvailable analysis profiles:")
    for name, description in profiles.items():
        print(f"  {name:12} - {description}")
    sys.exit(0)

def handle_create_config(options, config_manager):
    """Handle the --create-config option."""
    try:
        config_path = Path(options.create_config)
        config_manager.create_sample_config(config_path)
        print(f"Sample configuration file created: {config_path}")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Failed to create configuration file: {e}")
        sys.exit(1)

def handle_generate_test_mft(options):
    """Handle the --generate-test-mft option."""
    try:
        create_test_mft(
            output_path=options.generate_test_mft,
            num_records=options.test_records,
            test_type=options.test_type
        )
        print(f"Test MFT file created: {options.generate_test_mft}")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Failed to generate test MFT file: {e}")
        sys.exit(1)

def load_profile(options, config_manager):
    """Load profile from command line options, config file, or defaults."""
    profile = None
    
    if options.config_file:
        try:
            config_data = config_manager.load_config_file(options.config_file)
            profile = config_manager.load_profile_from_config(config_data, "from_file")
            logging.info(f"Loaded configuration from {options.config_file}")
        except Exception as e:
            logging.error(f"Failed to load configuration file: {e}")
            sys.exit(1)
    
    elif options.profile_name:
        profile = config_manager.get_profile(options.profile_name)
        if not profile:
            logging.error(f"Unknown profile: {options.profile_name}")
            logging.error(f"Available profiles: {', '.join(config_manager.list_profiles().keys())}")
            sys.exit(1)
        logging.info(f"Using profile: {options.profile_name}")
    
    else:
        default_config = find_config_file()
        if default_config:
            try:
                config_data = config_manager.load_config_file(default_config)
                profile = config_manager.load_profile_from_config(config_data, "default_file")
                logging.info(f"Loaded default configuration from {default_config}")
            except Exception as e:
                logging.warning(f"Failed to load default configuration file {default_config}: {e}")
                logging.warning("Continuing with command-line options only")
    
    return profile

def apply_profile_defaults(options, profile):
    """Apply profile defaults to options."""
    if profile:
        if not options.export_format:
            options.export_format = profile.export_format
        if options.compute_hashes is False and profile.compute_hashes:
            options.compute_hashes = profile.compute_hashes
        if options.verbosity == 0:
            options.verbosity = profile.verbosity
        if options.debug == 0:
            options.debug = profile.debug
        if options.chunk_size == 1000:
            options.chunk_size = profile.chunk_size

def setup_test_mode(options):
    """Setup test mode if enabled."""
    if options.test_mode:
        test_mft_file = "test_sample.mft"
        test_output_file = "test_output.csv"
        
        try:
            logging.warning(f"Test mode: Generating test MFT file {test_mft_file}")
            create_test_mft(
                output_path=test_mft_file,
                num_records=options.test_records,
                test_type=options.test_type
            )
            options.filename = test_mft_file
            if not options.output_file:
                options.output_file = test_output_file
            
            logging.warning(f"Test mode: Will analyze {test_mft_file} and output to {options.output_file}")
            
        except Exception as e:
            logging.error(f"Failed to generate test MFT for test mode: {e}")
            sys.exit(1)

def validate_options(options):
    """Validate command line options."""
    if not options.filename and not options.test_mode:
        print("Error: No input file specified. Use -f or --file to specify an MFT file.")
        return False

    if not options.output_file and not options.test_mode:
        print("Error: No output file specified. Use -o or --output to specify an output file.")
        return False

    if not options.export_format:
        options.export_format = "csv"

    try:
        validate_numeric_bounds(
            chunk_size=options.chunk_size,
            hash_processes=options.hash_processes,
            test_records=options.test_records,
            verbosity=options.verbosity,
            debug=options.debug
        )
        validate_export_format(options.export_format, options.output_file)
        
        # Skip path validation for stdout or test mode
        if options.output_file != "-" and not options.test_mode:
            validated_input, validated_output = validate_paths_secure(
                options.filename, options.output_file
            )
            options.filename = str(validated_input)
            options.output_file = str(validated_output)
        
        logging.info("All input validation checks passed successfully")
        return True
        
    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during validation: {e}")
        return False

async def run_analysis(options, profile):
    """Run the MFT analysis."""
    try:
        analyzer = MftAnalyzer(
            options.filename, 
            options.output_file, 
            options.debug, 
            options.verbosity, 
            options.compute_hashes, 
            options.export_format, 
            profile,
            options.chunk_size,
            options.multiprocessing_hashes,
            options.hash_processes
        )
        
        await analyzer.analyze()

        logger = logging.getLogger('analyzeMFT.cli')
        logger.warning(f"Analysis complete. Results written to {options.output_file}")

    except FileNotFoundError:
        logging.error(f"Error: The file '{options.filename}' was not found.")
        sys.exit(1)

    except PermissionError:
        logging.error(f"Error: Permission denied when trying to read '{options.filename}' or write to '{options.output_file}'.")
        sys.exit(1)

    except KeyboardInterrupt:
        logging.warning("Operation interrupted by user")
        sys.exit(1)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        
        if options.debug:
            import traceback
            logging.debug("Full traceback:", exc_info=True)
        
        sys.exit(1)

async def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    options = parser.parse_args()
    
    # Setup logging early
    setup_logging(options.verbosity, options.debug)
    
    config_manager = ConfigManager()

    # Handle special options that exit immediately
    if options.list_profiles:
        handle_list_profiles(config_manager)
    
    if options.create_config:
        handle_create_config(options, config_manager)
    
    if options.generate_test_mft:
        handle_generate_test_mft(options)

    # Load profile and apply defaults
    profile = load_profile(options, config_manager)
    apply_profile_defaults(options, profile)

    # Setup test mode
    setup_test_mode(options)

    # Validate options
    if not validate_options(options):
        parser.print_help()
        sys.exit(1)

    # Run analysis
    await run_analysis(options, profile)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("\nScript terminated by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")