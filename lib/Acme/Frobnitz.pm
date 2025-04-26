package Acme::Frobnitz;

use strict;
use warnings;
use IPC::System::Simple qw(capturex);
use Cwd qw(abs_path);
use File::Spec;
use File::stat;
use File::Basename;
use FindBin;
use POSIX qw(strftime);
use JSON;

our $VERSION = '0.05';

sub new {
    my ($class) = @_;
    return bless {}, $class;
}

sub call_main {
    my ($class, $hyperlink) = @_;
    die "No hyperlink provided.\n" unless $hyperlink;

    my $script_path = $class->_get_script_path("main.py");  # Locate main.py
    my $python_path = $class->_get_python_path();  # Find Python interpreter

    print "Executing: $python_path $script_path $hyperlink\n";

    my $output;
    eval {
        $output = capturex($python_path, $script_path, $hyperlink);
    };
    if ($@) {
        die "Error executing main.py with hyperlink $hyperlink: $@\n";
    }

    chomp($output);  # Clean up trailing newlines
    return $output;
}


# Load the JSON configuration file
sub _load_config {
    my $config_file = File::Spec->catfile($FindBin::Bin, '..', 'conf', 'config.json');
    open my $fh, '<', $config_file or die "Unable to open config file $config_file: $!\n";
    my $json_text = do { local $/; <$fh> };
    close $fh;

    my $config = decode_json($json_text);
    return $config;
}

# Get configuration for the current OS
sub _get_os_config {
    my $config = _load_config();
    my $osname = qx(uname -s);
    chomp($osname);

    die "Unsupported operating system: $osname\n" unless exists $config->{$osname};
    return $config->{$osname};
}

# Determine the Python interpreter path dynamically
sub _get_python_path {
    my ($class) = @_;
    my $os_config = _get_os_config();
    my $python_path = $os_config->{python_path};

    unless (-x $python_path) {
        die "Python interpreter not found or not executable at: $python_path\n";
    }

    return $python_path;
}

# Find the Python script path dynamically
sub _get_script_path {
    my ($class, $script_name) = @_;
    my $os_config = _get_os_config();
    my $base_dir = $os_config->{base_dir};
    my $script_path = File::Spec->catfile($base_dir, 'bin', $script_name);

    unless (-f $script_path) {
        die "Python script $script_path does not exist.\n";
    }

    return $script_path;
}

sub download {
    my ($class, $hyperlink) = @_;
    die "No hyperlink provided.\n" unless $hyperlink;

    my $script_path = $class->_get_script_path("call_download.py");
    my $python_path = $class->_get_python_path();
    print "DEBUG: Running command: $python_path $script_path $hyperlink\n";

    my $output;
    eval {
        $output = capturex($python_path, $script_path, $hyperlink);
    };
    if ($@) {
        die "Error executing $script_path with hyperlink $hyperlink: $@\n";
    }

    # Debugging Output: Print Full Response
    print "DEBUG FULL OUTPUT FROM PYTHON SCRIPT:\n";
    my @lines = split /\n/, $output;
    foreach my $i (0..$#lines) {
        print "[$i]: $lines[$i]\n";  # Print each line with an index
    }
    print "END DEBUG OUTPUT\n";

    # Find the last valid filename
    my $filename;
    foreach my $line (reverse @lines) {  # Reverse order, so we find the last one
        print "DEBUG SCANNING LINE: '$line'\n";  # Print each line we check
        if ($line =~ m{(["']?)([\w./ -]+\.(mp4|mkv|webm|mov|avi|flv|m4v|wmv))\1$}i) {
            $filename = $2;  # Capture only the valid filename
            print "DEBUG MATCH FOUND: '$filename'\n";  # Confirm we captured it
            last;
        }
    }

    if (!$filename) {
        die "ERROR: No valid video filename found in download output!\n";
    }

    # Print extracted filename for debugging
    print "DEBUG EXTRACTED FILENAME: '$filename'\n";

    return $filename;  # Return actual filename, NOT "DEBUG_COMPLETE"
}






# Add watermark by invoking the Python watermark script directly
sub add_watermark {
    my ($class, $input_video) = @_;
    die "Input video file not provided.\n" unless $input_video;

    my $script_path = $class->_get_script_path("call_watermark.py");
    my $python_path = $class->_get_python_path();
    print "Running command: $python_path $script_path $input_video\n";
    $DB::single = 1; 
    my $output;
    eval {
        $output = capturex($python_path, $script_path, $input_video);
    };
    if ($@) {
        die "Error adding watermark with $script_path: $@\n";
    }

    chomp($output); # Remove trailing newlines from Python output
    return $output;
}

sub add_basic_captions {
    my ($class, $input_video) = @_;
    die "Input video file not provided.\n" unless $input_video;


    my $script_path = $class->_get_script_path("call_captions.py");
    my $python_path = $class->_get_python_path();
    print "Running command: $python_path $script_path $input_video \n";
    $DB::single = 1; 
    my $output;
    eval {
        $output = capturex($python_path, $script_path, $input_video);
    };
    if ($@) {
        die "Error adding captions with $script_path: $@\n";
    }

    chomp($output); # Remove trailing newlines from Python output
    return $output;
}


sub make_clips {
    my ($class, $input_video, $yaml_file) = @_;
    die "Input video file not provided.\n" unless $input_video;
    die "YAML file not provided.\n" unless $yaml_file;

    my $script_path = $class->_get_script_path("call_clips.py");  
    my $python_path = $class->_get_python_path();
    print "Running command: $python_path $script_path $input_video $yaml_file\n";

    my $output;
    eval {
        $output = capturex($python_path, $script_path, $input_video, $yaml_file);
    };
    if ($@) {
        die "Error making clips with $script_path: $@\n";
    }

    chomp($output);
    return $output;
}

sub call_dispatch {
    my ($class, $url) = @_;
    
    die "url file not provided.\n" unless $url;

    my $script_path = $class->_get_script_path("dispatch.py");  
    my $python_path = $class->_get_python_path();
    print "Running command: $python_path $script_path  $url\n";
    my $output;
    eval {
        $output = capturex($python_path, $script_path, $url);
    };
    if ($@) {
        die "Error making clips with $script_path: $@\n";
    }

    chomp($output);
    return $output;
}


sub continue_tasks {
    my ($class, $input_video) = @_;
    die "Input video file not provided.\n" unless $input_video;


    my $script_path = $class->_get_script_path("continue_tasks.py");
    my $python_path = $class->_get_python_path();
    print "Running command: $python_path $script_path $input_video \n";
    $DB::single = 1; 
    my $output;
eval {
    $output = capturex($python_path, $script_path, $input_video);
};
if ($@) {
    warn "🔥 Python script failed!\n";
    warn "Script: $script_path\n";
    warn "Input : $input_video\n";
    warn "Error : $@\n";
    die "Error adding captions with $script_path\n";
}

    if ($@) {
        die "Error adding captions with $script_path: $@\n";
    }

    chomp($output); # Remove trailing newlines from Python output
    return $output;
}






# Verify the downloaded file
sub verify_file {
    my ($class, $file_path) = @_;
    die "File path not provided.\n" unless $file_path;

    my $abs_path = abs_path($file_path) // $file_path;
    #$DB::single = 1; 
    if (-e $abs_path) {
        print "File exists: $abs_path\n";

        # File size
        my $size = -s $abs_path;
        print "File size: $size bytes\n";

        # File permissions
        my $permissions = sprintf "%04o", (stat($abs_path)->mode & 07777);
        print "File permissions: $permissions\n";

        # Last modified time
        my $mtime = stat($abs_path)->mtime;
        print "Last modified: ", strftime("%Y-%m-%d %H:%M:%S", localtime($mtime)), "\n";

        # Owner and group
        my $uid = stat($abs_path)->uid;
        my $gid = stat($abs_path)->gid;
        print "Owner UID: $uid, Group GID: $gid\n";

        return 1; # Verification success
    } else {
        print "File does not exist: $abs_path\n";
        my $dir = dirname($abs_path);

        # Report directory details
        print "Inspecting directory: $dir\n";
        opendir my $dh, $dir or die "Cannot open directory $dir: $!\n";
        my @files = readdir $dh;
        closedir $dh;

        print "Directory contents:\n";
        foreach my $file (@files) {
            next if $file =~ /^\.\.?$/; # Skip . and ..
            my $file_abs = File::Spec->catfile($dir, $file);
            my $type = -d $file_abs ? 'DIR ' : 'FILE';
            my $size = -s $file_abs // 'N/A';
            print "$type - $file (Size: $size bytes)\n";
        }

        return 0; # Verification failed
    }
}

1; # End of Acme::Frobnitz

