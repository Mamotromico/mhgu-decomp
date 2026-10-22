struct S_600c22b4 {
    unsigned char pad_0x0[0x1428];
    unsigned int field_0x1428;
};

extern "C" float func_600c22b4(S_600c22b4 *s) {
    return *reinterpret_cast<float *>(s->field_0x1428 + 0x5b8u);
}