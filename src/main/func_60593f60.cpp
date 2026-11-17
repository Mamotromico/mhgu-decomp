extern "C" int func_6054533c(int, int, int);

extern "C" void func_60593f80(char *);

extern "C" int func_60593f60(char *p)
{
    func_60593f80(p);
    return func_6054533c(*(int *)(p + 0x24), 0xa, *(unsigned char *)(p + 0xb8));
}