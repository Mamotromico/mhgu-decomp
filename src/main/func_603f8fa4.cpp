extern "C" int func_603f7c10(void *);

struct S {
    char pad0[0x48];
    int f48;
    int f4c;
    unsigned char f50;
    unsigned char f51;
};

extern "C" int func_603f8fa4(struct S *p) {
    p->f48 = -1;
    *(unsigned char *)((char *)p + 0x51) = 0;
    *(unsigned char *)((char *)p + 0x50) = 0xff;
    p->f4c = -1;
    return func_603f7c10(p);
}