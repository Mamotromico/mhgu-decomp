extern "C" void func_603b05d8(void *self, void *a1, short a2);

extern "C" void func_603b0858(char *self, unsigned a1, int a2)
{
    func_603b05d8(self, (void *)a1, (short)(-a2));
    *(unsigned char *)(self + 0x167d) = 1;
}