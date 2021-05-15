//      with open(abd) as file:
//          pass
//
//  Gets rewritten as
//
//      file = open(abd);
//      defer([&file]() { close(file); });
//

template<typename Callable>
class defer {
public:
    defer(Callable deleter):
        deleter(deleter)
    {}

    ~defer() {
        deleter()
    }

private:
    Callable deleter
};
