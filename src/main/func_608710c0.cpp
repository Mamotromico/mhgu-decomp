struct S {
    unsigned char pad[0x460];
    float f;
};

extern "C" float func_608710c0(const struct S *p) {
    return *(const float *)((const char *)p + 0x460);
}