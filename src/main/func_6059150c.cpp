extern "C" void func_6056e4d8(void *);
extern "C" void func_6059152c(void *);

extern "C" void func_6059150c(char *p)
{
    func_6056e4d8(p);
    func_6059152c(p);
    *(unsigned *)(p + 0x50) = 0;
}