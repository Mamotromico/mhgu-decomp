struct Inner_604a1b50 {
    char pad_00[8];
    unsigned int field_08;
};

struct Outer_604a1b50 {
    char pad_0000[0x136c];
    struct Inner_604a1b50 *field_136c;
};

extern "C" unsigned char func_604a1b50(struct Outer_604a1b50 *param_1)
{
    struct Inner_604a1b50 *p = param_1->field_136c;
    return p ? (unsigned char)p->field_08 : 0xff;
}