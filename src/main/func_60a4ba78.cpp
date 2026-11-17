extern "C" void func_60a4ad5c(void *);

extern "C" void func_60a4ba78(void *p)
{
    func_60a4ad5c(p);
    *(unsigned *)((char *)p + 0xa4) |= 2;
}