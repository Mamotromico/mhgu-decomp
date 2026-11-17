extern "C" {
extern char D_6188ca48[];
}

struct S602a1bc0_0 {
    char pad0[0x67];
    unsigned char f67;
};

struct S602a1bc0_1 {
    char pad0[0x0];
    S602a1bc0_0 *p0;
};

extern "C" int func_602a1bc0(void)
{
    S602a1bc0_1 *outer = (S602a1bc0_1 *)D_6188ca48;
    S602a1bc0_0 *inner = outer->p0;
    return inner->f67 == 1;
}