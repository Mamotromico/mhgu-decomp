extern "C" void func_6056e558(unsigned *base, unsigned value, unsigned count);

extern "C" void func_605d19ac(unsigned *self)
{
    unsigned v = *(unsigned *)((char *)self + 0x2c);
    func_6056e558(self, v, 4);
}