extern "C" void func_609dcaec(void *dst, const void *src);

extern "C" void func_608a62fc(char *self, const void *src)
{
    *(const void **)(self + 0x68) = src;
    func_609dcaec(self + 0x90, src);
    func_609dcaec(self + 0x130, src);
}