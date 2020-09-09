//usr/bin/gcc-8 "$0" -o "$0".bin && exec ./"$0".bin

// Global
struct GlobalPoint {
    float x;
    float y;
} point1, point2;

// Normal C definition
struct Point {
    float x;
    float y;
};

// Struct def + typedef
typedef struct MergedTypedefPoint {
    float x;
    float y;
} MergedTypedefPoint;

// Anononymous struct named with typedef
typedef struct {
    float x;
    float y;
} TypedefAnonymousPoint;

// Typedef struct definition
typedef struct Point TypedefPoint;

// struct with bit fields
struct PackedFlag {
    unsigned int f1:1;
    unsigned int f2:1;
    unsigned int f3:1;
    unsigned int f4:1;
    unsigned int f5:1;
    unsigned int f6:1;
    unsigned int f7:1;
    unsigned int f8:1;
};

int main(int argc, const char* argv[]) {
    struct Point          p1;
    MergedTypedefPoint    p2;
    TypedefAnonymousPoint p3;
    point1.x = 0.f;

    return 0;
};