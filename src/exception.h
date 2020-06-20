#include <spdlog/fmt/bundled/core.h>


// Exception that shows the backtrace when .what() is called
class Exception: public std::exception{
public:
    template<typename ... Args>
    Exception(const char* fmt, const Args& ... args):
        message(fmt::format(fmt, args...))
    {}

    const char* what() const noexcept final { return message.c_str(); }

private:
    std::string message;
};

class ValueError: public Exception {
public:
    template<typename ... Args>
    ValueError(const char* fmt, const Args& ... args):
        Exception(fmt, args...)
    {}
};
