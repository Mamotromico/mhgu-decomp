extern "C" int func_612d6bdc(char *a, int b, int *c);

extern "C" void func_612d6bbc(char *a, int b, int c)
{
    int tmp = c;
    func_612d6bdc(a + 0x10, b, &tmp);
}