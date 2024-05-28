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

// Entry_type: Differentiates directories and various file types.
// Currently only has one generic file type.
enum Entry_type { 
    Unknown = -1,
    Directory = 0,
    File = 1
};

// An Entry is a directory or a file with the following attributes:
// - path: fs::path (->string). The entry's absolute path.
// - name: string. The entry name. Cannot contain the " character.
// - type: Entry_type (->int). The enum of the entry type.
// It is ordered such that directories are before files (compare_type), 
// then alphabetically (compare_name).
struct Entry {
    fs::path path;
    std::string name;
    Entry_type type;

    std::strong_ordering operator<=>(const Entry& other) const {
        auto compare_name = name <=> other.name; 
        auto compare_type = type <=> other.type; 
        if (compare_type != 0) return compare_type;
        return compare_name;
    }
};

// Recursively traverses filesystem tree, printing entry names, types, and sizes.
// The sizes of directories are calculated recursively.
std::uintmax_t traverse(struct Entry entry, int depth)
{
    std::uintmax_t size = 0;

    std::cout << "[";
    std::cout << "\"" << entry.name << "\",";
    std::cout << "\"" << entry.type << "\"";

    if(entry.type == Directory) 
    {
        if(depth != 0) 
        {
            std::set<struct Entry> children;

            for(const auto& child : fs::directory_iterator{entry.path})
            {
                fs::path child_path = child.path();
                struct Entry child_entry = {
                    .path = child_path,
                    .name = child_path.filename(),
                    .type = (child.is_directory()) ? Directory : File
                };
                children.insert(child_entry);
            }
            for(const Entry &child_entry : children)
            {
                std::cout << ",";
                size += traverse(child_entry, depth - 1);
            }
        }
    } 
    else if(entry.type == File)
    {
        try {
            size = fs::file_size(entry.path);
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
    const struct Entry base = { 
	.path = base_path,
        .name = base_path.filename(),
        .type = Directory,
    };

    traverse(base, max_depth);
    std::cout << "\n";
}
