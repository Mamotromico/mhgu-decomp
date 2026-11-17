extern char D_61834b54[];

extern "C" void func_613ef744(void *);

extern "C" void func_6135de28(char *p)
{
    *(char **)p = &D_61834b54[8];
    *(int *)(p + 0x50) = 0;
    func_613ef744(p);
}