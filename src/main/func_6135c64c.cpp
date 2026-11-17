extern "C" void func_613606fc(void *);

extern "C" void func_6135c64c(char *p)
{
    func_613606fc(p);
    *(unsigned *)(p + 0x78) = 0;
    *(unsigned *)(p + 0x7c) = 0;
    *(unsigned char *)(p + 0x80) = 0;
}