extern char D_61786f64[];

struct S {
    char pad0[0x8];
};

extern "C" void func_607ca424(char *p)
{
    *(char **)(p + 0x0) = D_61786f64 + 0x8;
    *(unsigned char *)(p + 0x8) = 0;
    *(unsigned char *)(p + 0x9) = 0;
    *(unsigned *)(p + 0xc) = 0;
    *(unsigned *)(p + 0x10) = 0;
}