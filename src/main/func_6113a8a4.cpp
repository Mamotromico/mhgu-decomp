struct S_6113a8a4 {
    unsigned char pad_00[0x44];
    float field_44;
    unsigned char pad_48[0x10a8];
    float field_10f0;
};

extern "C" float func_6113a8a4(S_6113a8a4 *p) {
    float *q = &p->field_10f0;
    float a = p->field_44;
    return a - *q;
}