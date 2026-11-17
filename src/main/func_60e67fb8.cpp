extern "C" void func_600c9eb0(void *);

extern "C" void func_60e67fb8(void *self)
{
    func_600c9eb0(self);
    *(unsigned *)((char *)self + 0x170) = 2;
}