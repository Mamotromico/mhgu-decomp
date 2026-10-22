extern "C" int func_601ac470(int a, int b, int c)
{
    int base = a + 6 * b + c;
    ((char *)base)[9] = 1;
    return base;
}