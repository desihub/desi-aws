#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <map>

namespace fs = std::filesystem;

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
    if(argc <= 1) {
        std::cout << "\n";
        std::cout << "Filesystem JSON tree generator" << "\n";
        std::cout << "usage: gen <path> [max depth]" << "\n";
        std::cout << "| <path>: required; path to base directory" << "\n";
        std::cout << "| [max depth]: optional; default unlimited (-1); maximum search depth" << "\n";
        std::cout << "output: [ <name>, <child 1>, <child 2>, ... , <type>, <size> ]" << "\n";
        std::cout << "| <name>: name of file or directory" << "\n";
        std::cout << "| <type>: type of file or directory" << "\n";
        std::cout << "| <child N>: recursive structure" << "\n";
        std::cout << "\n";
        return 0;
    }

    const std::string base_directory = argv[1];

    int max_depth = (argc >= 3) ? atoi(argv[2]) : -1;

    const fs::path base_path{base_directory};
    const struct Entry_key base_key = { 
        .entry_name = base_path.filename(),
        .entry_type = directory,
    };

    hierarchy(base_path, base_key, max_depth);
    std::cout << "\n";
}
