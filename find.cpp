#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <map>
#include <boost/program_options.hpp>

namespace fs = std::filesystem;
namespace po = boost::program_options;

// ========
// Filesystem JSON tree generator
//
// Generates a JSON tree of the files and directories, 
// including their sizes (in bytes), recursively calculated for directories
// ========

// Entry: A directory or file

// Entry_type: Differentiates directories and various file types.
// Currently only has one generic file type.
enum Entry_type { 
    directory = 0,
    file = 1
};

// Entry_key: For sorting entries.
// Currently puts directories before files (compare_type), then alphabetically (compare_name).
struct Entry_key {
    std::string entry_name;
    Entry_type entry_type;

    std::strong_ordering operator<=>(const Entry_key& other) const {
        auto compare_name = entry_name <=> other.entry_name; 
        auto compare_type = entry_type <=> other.entry_type; 
        if (compare_type != 0) return compare_type;
        return compare_name;
    }
};


std::uintmax_t hierarchy(fs::path path, struct Entry_key key, int depth)
{
    std::uintmax_t size = 0;

    std::cout << "[";
    std::cout << "\"" << key.entry_name << "\"";

    if(key.entry_type == directory) {
        std::cout << ",0";

        if(depth != 0) 
        {
            std::map<struct Entry_key, fs::path> sorted_dir;

            for(const auto& dir_entry : fs::directory_iterator{path})
            {
                fs::path entry_path = dir_entry.path();
                struct Entry_key entry_key = {
                    .entry_name = entry_path.filename(),
                    .entry_type = (dir_entry.is_directory()) ? directory : file,
                };

                sorted_dir[ entry_key ] = entry_path;
            }
            for(const auto&[ entry_key, entry_path ] : sorted_dir)
            {
                std::cout << ",";
                size += hierarchy(entry_path, entry_key, depth - 1);
            }
        }
    } else {
        std::cout << ",1";
        try {
            size = fs::file_size(path);
        }
        catch (const std::exception& e){
            std::cerr << "Exception: " << e.what() << "\n";
            size = 0;
        }
    }

    std::cout << "," << size;
    std::cout << "]";
    return size;
}

int main(int argc, char* argv[])
{
    int max_depth;
    std::string base_directory;

    // Program description and arguments
    
    po::options_description options_description(
        "\n"
        "Filesystem JSON tree generator \n" 
        "  Generates a JSON tree of the files and directories, \n" 
        "  including their sizes (in bytes), recursively calculated for directories. \n" 
        "\n"
        "Each node in tree has the structure \n"
        "[ <name>, <child 1>, <child 2>, ... , <type>, <size> ] \n" 
        "  <name>   \tname of file or directory \n" 
        "  <child N>\tchild node for child file or directory \n" 
        "  <type>   \t0 for directory, 1 for file \n" 
        "  <size>   \tsize of file or directory (including children), in bytes \n" 
        "\n"
        "Options"
    );
    options_description.add_options()
        ("help", "prints this help message")
        ("root", po::value<std::string>(&base_directory)->default_value("."), "path to the root directory")
        ("depth", po::value<int>(&max_depth)->default_value(-1), "maximum crawl depth; -1=infinite")
    ;
    po::positional_options_description positional_options;
    positional_options.add("root", -1);

    // Parse command line arguments
    po::variables_map variables_map;
    po::store(
        po::command_line_parser(argc, argv)
            .options(options_description)
            .positional(positional_options)
            .run(), 
        variables_map
    );
    po::notify(variables_map);
    // Print description with --help
    if (variables_map.count("help")) {
        std::cerr << options_description << "\n";
        return 1;
    }

    const fs::path base_path{base_directory};
    const struct Entry_key base_key = { 
        .entry_name = base_path.filename(),
        .entry_type = directory,
    };

    hierarchy(base_path, base_key, max_depth);
    std::cout << "\n";
}
