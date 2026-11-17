extern "C" {
void func_6056e4d8(void *);
void func_605b5e80(void *);
void func_605b5f84(void *);
}

extern "C" void func_605b5e58(char *p)
{
    func_6056e4d8(p);
    func_605b5e80(p);
    func_605b5f84(p);
    *(unsigned *)(p + 0xec) = 0;
}