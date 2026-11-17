extern "C" void func_601fed90(void *p);

struct S4 {
    unsigned char pad0[0xfe8];
    unsigned int f_fe8;
    unsigned char pad_feC[0x3266 - 0xfeC];
    unsigned short f_3266;
};

struct S5 {
    unsigned char pad0[0x30];
    unsigned short f_30;
    unsigned char pad32[0x98 - 0x32];
    unsigned short f_98;
};

extern "C" void func_60203e4c(void *a0, struct S4 *a1) {
    func_601fed90(a0);
    struct S5 *s = (struct S5 *)a0;
    s->f_30 = a1->f_fe8;
    s->f_98 = a1->f_3266;
}