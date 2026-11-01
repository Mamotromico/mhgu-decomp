extern "C" int func_600b75cc(unsigned int a, unsigned int b, unsigned int c)
{
    unsigned int q = b / 100;
    unsigned int rem = b % 100;
    return rem < c ? 1 : 0;
}