//usr/bin/gcc-8 "$0" -o "$0".bin && exec ./"$0".bin

// Global
union GlobalIorF {
    int x;
    float y;
} point1, point2;

// Normal C definition
union IorF {
    int x;
    float y;
};

// Struct def + typedef
typedef union MergedTypedefIorF {
    int x;
    float y;
} MergedTypedefIorF;

// Anononymous struct named with typedef
typedef union {
    int x;
    float y;
} TypedefAnonymousIorF;

// Typedef struct definition
typedef union IorF TypedefIorF;

int main(int argc, const char* argv[]) {
    union IorF          p1;
    MergedTypedefIorF    p2;
    TypedefAnonymousIorF p3;
    point1.x = 0.f;

    return 0;
};