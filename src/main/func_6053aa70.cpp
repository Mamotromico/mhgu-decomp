struct S {
    char pad[0x1c];
    float value;
};

extern "C" void func_6053aa70(const S *s, float *out, float scale) {
    *out += s->value * scale;
}