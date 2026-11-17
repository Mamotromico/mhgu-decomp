extern "C" void func_613ef7e0(void *p, unsigned x);

extern "C" void func_6134c970(char *p)
{
    *(unsigned char *)(p + 0x370) = 1;
    func_613ef7e0(p + 0x340, 2);
}