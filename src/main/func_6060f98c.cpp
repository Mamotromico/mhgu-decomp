typedef struct Inner {
    unsigned char pad0[0x7c];
    int value;
} Inner;

typedef struct Outer {
    unsigned char pad0[0x4c];
    int value;
    Inner *inner;
} Outer;

extern "C" void func_6060f98c(Outer *outer, int value)
{
    outer->value = value;
    Inner *inner = outer->inner;
    if (inner != 0) {
        inner->value = value;
    }
}