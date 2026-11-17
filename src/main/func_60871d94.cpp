extern "C" void func_60870800(void *self, unsigned value);

extern "C" void func_60871d94(void *self, unsigned value)
{
    *(unsigned *)((char *)self + 0x490) = value;
    func_60870800(self, 3);
}