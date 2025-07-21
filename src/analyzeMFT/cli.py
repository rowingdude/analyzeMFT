import asyncio
import logging
from optparse import OptionParser, OptionGroup
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

async def main():
    # Setup basic logging configuration (will be refined by analyzer)
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    parser = OptionParser(usage="usage: %prog -f <mft_file> -o <output_file> [options]",
                          version=f"%prog {VERSION}")
    parser.add_option("-f", "--file", dest="filename",
                      help="MFT file to analyze", metavar="FILE")
    parser.add_option("-o", "--output", dest="output_file",
                      help="Output file", metavar="FILE")
    
    export_group = OptionGroup(parser, "Export Options")
    export_group.add_option("--csv", action="store_const", const="csv", dest="export_format",
                            help="Export as CSV (default)")
    export_group.add_option("--json", action="store_const", const="json", dest="export_format",
                            help="Export as JSON")
    export_group.add_option("--xml", action="store_const", const="xml", dest="export_format",
                            help="Export as XML")
    export_group.add_option("--excel", action="store_const", const="excel", dest="export_format",
                            help="Export as Excel")
    export_group.add_option("--body", action="store_const", const="body", dest="export_format",
                            help="Export as body file (for mactime)")
    export_group.add_option("--timeline", action="store_const", const="timeline", dest="export_format",
                            help="Export as TSK timeline")
    export_group.add_option("--l2t", action="store_const", const="l2t", dest="export_format",
                            help="Export as log2timeline CSV")
    export_group.add_option("--sqlite", action="store_const", const="sqlite", dest="export_format",
                            help="Export as SQLite database")
    export_group.add_option("--tsk", action="store_const", const="tsk", dest="export_format",
                            help="Export as TSK bodyfile format")
    
    parser.add_option_group(export_group)

    verbosity_group = OptionGroup(parser, "Verbosity Options")
    verbosity_group.add_option("-v", action="count", dest="verbosity",
                               help="Increase output verbosity (can be used multiple times)", default=0)
    verbosity_group.add_option("-d", action="count", dest="debug",
                               help="Increase debug output (can be used multiple times)", default=0)
    parser.add_option_group(verbosity_group)

    performance_group = OptionGroup(parser, "Performance Options")
    performance_group.add_option("--chunk-size", dest="chunk_size", type="int", default=1000,
                                help="Number of records to process in each chunk (default: 1000)")
    performance_group.add_option("-H", "--hash", action="store_true", dest="compute_hashes",
                                help="Compute hashes (MD5, SHA256, SHA512, CRC32)", default=False)
    performance_group.add_option("--no-multiprocessing-hashes", action="store_false", dest="multiprocessing_hashes",
                                help="Disable multiprocessing for hash computation", default=True)
    performance_group.add_option("--hash-processes", dest="hash_processes", type="int",
                                help="Number of processes for hash computation (default: auto-detect)")
    parser.add_option_group(performance_group)
    
    # Configuration options
    config_group = OptionGroup(parser, "Configuration Options")
    config_group.add_option("-c", "--config", dest="config_file", metavar="FILE",
                           help="Load configuration from JSON/YAML file")
    config_group.add_option("--profile", dest="profile_name", metavar="NAME",
                           help="Use predefined analysis profile (default, quick, forensic, performance)")
    config_group.add_option("--list-profiles", action="store_true", dest="list_profiles",
                           help="List available analysis profiles and exit")
    config_group.add_option("--create-config", dest="create_config", metavar="FILE",
                           help="Create a sample configuration file and exit")
    parser.add_option_group(config_group)
    
    # Test options
    test_group = OptionGroup(parser, "Test Options")
    test_group.add_option("--test-mode", action="store_true", dest="test_mode",
                         help="Generate test MFT file and run analysis")
    test_group.add_option("--generate-test-mft", dest="generate_test_mft", metavar="FILE",
                         help="Generate a test MFT file and exit")
    test_group.add_option("--test-records", dest="test_records", type="int", default=1000,
                         help="Number of records in test MFT (default: 1000)")
    test_group.add_option("--test-type", dest="test_type", choices=["normal", "anomaly"],
                         default="normal", help="Type of test MFT to generate (normal, anomaly)")
    parser.add_option_group(test_group)

    (options, args) = parser.parse_args()
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    
    # Handle special actions first
    if options.list_profiles:
        profiles = config_manager.list_profiles()
        print("\nAvailable analysis profiles:")
        for name, description in profiles.items():
            print(f"  {name:12} - {description}")
        sys.exit(0)
    
    if options.create_config:
        try:
            config_path = Path(options.create_config)
            config_manager.create_sample_config(config_path)
            print(f"Sample configuration file created: {config_path}")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Failed to create configuration file: {e}")
            sys.exit(1)
    
    if options.generate_test_mft:
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
    
    # Load configuration if specified
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
        # Try to find default configuration file
        default_config = find_config_file()
        if default_config:
            try:
                config_data = config_manager.load_config_file(default_config)
                profile = config_manager.load_profile_from_config(config_data, "default_file")
                logging.info(f"Loaded default configuration from {default_config}")
            except Exception as e:
                logging.warning(f"Failed to load default configuration file {default_config}: {e}")
                logging.warning("Continuing with command-line options only")
    
    # Apply configuration profile settings, with CLI options taking precedence
    if profile:
        # Update options with profile values where CLI didn't specify them
        if not options.export_format:
            options.export_format = profile.export_format
        if options.compute_hashes is False and profile.compute_hashes:
            options.compute_hashes = profile.compute_hashes
        if options.verbosity == 0:
            options.verbosity = profile.verbosity
        if options.debug == 0:
            options.debug = profile.debug
        if options.chunk_size == 1000:  # Default value
            options.chunk_size = profile.chunk_size
    
    # Handle test mode
    if options.test_mode:
        test_mft_file = "test_sample.mft"
        test_output_file = "test_output.csv"
        
        try:
            # Generate test MFT
            logging.warning(f"Test mode: Generating test MFT file {test_mft_file}")
            create_test_mft(
                output_path=test_mft_file,
                num_records=options.test_records,
                test_type=options.test_type
            )
            
            # Override options for test
            options.filename = test_mft_file
            if not options.output_file:
                options.output_file = test_output_file
            
            logging.warning(f"Test mode: Will analyze {test_mft_file} and output to {options.output_file}")
            
        except Exception as e:
            logging.error(f"Failed to generate test MFT for test mode: {e}")
            sys.exit(1)
    
    if not options.filename:
        parser.print_help()
        logging.error("\nError: No input file specified. Use -f or --file to specify an MFT file.")
        sys.exit(1)

    if not options.output_file:
        parser.print_help()
        logging.error("\nError: No output file specified. Use -o or --output to specify an output file.")
        sys.exit(1)

    # Default to CSV if no format specified
    if not options.export_format:
        options.export_format = "csv"  

    # ========== INPUT VALIDATION ==========
    # Comprehensive validation of all inputs before processing
    try:
        # Validate numeric parameters
        validate_numeric_bounds(
            chunk_size=options.chunk_size,
            hash_processes=options.hash_processes,
            test_records=options.test_records,
            verbosity=options.verbosity,
            debug=options.debug
        )
        
        # Validate export format and dependencies
        validate_export_format(options.export_format, options.output_file)
        
        # Validate and secure file paths
        validated_input, validated_output = validate_paths_secure(
            options.filename, options.output_file
        )
        
        # Update options with validated paths
        options.filename = str(validated_input)
        options.output_file = str(validated_output)
        
        logging.info("All input validation checks passed successfully")
        
    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during validation: {e}")
        sys.exit(1)
    # ========== END INPUT VALIDATION ==========

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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("\nScript terminated by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")