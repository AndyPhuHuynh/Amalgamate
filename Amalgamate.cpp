#include <fstream>
#include <iostream>
#include <regex>
#include <set>
#include <string>
#include <string_view>

struct SearchResult {
    bool successful;
    std::string result;
};

class Parser {
private:
    inline static const std::regex localIncludeRegex = std::regex(R"SEC(^\s*#\s*include\s*"([^">]+)")SEC");
    inline static const std::regex pragmaOnceRegex = std::regex(R"SEC(^\s*#\s*pragma\s*once\b)SEC");
public:
    std::set<std::string> alreadyIncluded;

    static void generate_header(std::ofstream& output, const std::string& str) {
        constexpr int total_width = 118;
        constexpr int comment_prefix_width = 2;
        int content_width = total_width - comment_prefix_width;

        int left_padding = (content_width - str.size()) / 2;
        int right_padding = content_width - str.size() - left_padding;

        output << "//" << std::string(content_width, '-') << "\n";
        output << "//" << std::string(left_padding, '-') << str << std::string(right_padding, '-') << "\n";
        output << "//" << std::string(content_width, '-') << "\n";
    }

    SearchResult is_local_include(const std::string& line) {
        std::smatch match;
        SearchResult res;
        res.successful = std::regex_search(line, match, localIncludeRegex);
        if (res.successful) {
            res.result = match[1];
        }
        return res;
    }

    SearchResult is_pragma_once(const std::string& line) {
        SearchResult res;
        res.successful = std::regex_search(line, pragmaOnceRegex);
        return res;
    }

    void parse_include(std::ofstream& output, const std::string includePath) {
        auto includeFile = std::ifstream(includePath);
        parse_file(output, includePath, includeFile);
    }

    void parse_file(std::ofstream& output, const std::string& inputPath, std::ifstream& input) {
        bool isFirstLine = true;
        std::string line;
        
        generate_header(output, inputPath);
        output << "\n";
        while (std::getline(input, line)) {
            if (isFirstLine) {
                isFirstLine = false;
                // Remove UTF-8 BOM if present
                const std::string utf8_bom = "\xEF\xBB\xBF";
                if (line.compare(0, utf8_bom.size(), utf8_bom) == 0) {
                    line.erase(0, utf8_bom.size());
                }
            }

            if (SearchResult res = is_local_include(line); res.successful) {
                if (!alreadyIncluded.contains(res.result)) {
                    parse_include(output, res.result);
                } else {
                    continue;
                }
            } else if (is_pragma_once(line).successful) {
                alreadyIncluded.emplace(inputPath);
            } else {
                output << line << "\n";
            }
        }
        generate_header(output, "END " + inputPath);
        output << "\n";
    }
};

int main() {
    const std::string inputName = "Masterfile.hpp";

    auto output = std::ofstream("ArgonMaster.hpp");
    auto input = std::ifstream(inputName);

    Parser parser;
    parser.parse_file(output, inputName, input);
}