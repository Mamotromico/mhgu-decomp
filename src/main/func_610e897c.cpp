struct Inner {
    char pad0[0x10];
    float value;
};

struct Outer {
    char pad0[0xcacc];
    Inner* inner;
};

extern "C" void func_610e897c(Outer* outer, float x) {
    outer->inner->value = 1.0f / x;
}