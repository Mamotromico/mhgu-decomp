extern "C" void func_6050d078(char *p, unsigned a, int b)
{
    unsigned *field = (unsigned *)(p + 0x3dc);
    unsigned v = *field;
    unsigned r = (b != 0) ? (v | a) : (v & ~a);
    *field = r;
}