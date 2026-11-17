extern "C" int func_6027bcd0(void);

extern "C" void func_602c193c(void *p)
{
    if (func_6027bcd0() == 1) {
        *(unsigned int *)((char *)p + 0x27bc) = 0x42b40000;
    }
}