struct S {
    float f;
    char pad[0x46C];
};

extern "C" float func_608710cc(const S *p) {
    return p[1].f;
}