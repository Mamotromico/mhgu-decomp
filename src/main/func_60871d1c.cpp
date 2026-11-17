extern "C" int func_60870800(void *self, int val);

struct S {
    char pad[0x45c];
    float f;
};

extern "C" int func_60871d1c(S *self, float v) {
    *(float *)((char *)self + 0x45c) = v;
    return func_60870800(self, 3);
}