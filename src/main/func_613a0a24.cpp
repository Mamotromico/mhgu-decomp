extern "C" {

extern char D_616bdb44[];

struct S {
    char pad0[4];
    int f4;
    int f8;
    int fc;
};

void func_613a0a24(struct S *p)
{
    *(int *)((char *)p + 4) = 0xfd;
    *(int *)((char *)p + 8) = 0;
    *(int *)((char *)p + 12) = *(int *)(D_616bdb44 + 0);
}

}