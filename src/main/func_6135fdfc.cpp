extern char D_61834c7c[];

extern "C" void func_613ef744(void *);

extern "C" void func_6135fdfc(char *p)
{
    *(char **)(p + 0x0) = &D_61834c7c[8];
    *(unsigned *)(p + 0x44) = 0;
    func_613ef744(p);
}