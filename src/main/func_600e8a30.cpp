extern "C" void func_600e8a30(unsigned char *p, int i, int j)
{
    unsigned char *q = p + 0x244;
    unsigned char tmp = q[i];
    q[i] = q[j];
    q[j] = tmp;
}