extern "C" void func_6130a8fc(void *dst, int val);

extern "C" void func_6138867c(char *self, int a, int b)
{
    *(int *)(self + 0x74) = a;
    func_6130a8fc(self + 0x68, b);
}