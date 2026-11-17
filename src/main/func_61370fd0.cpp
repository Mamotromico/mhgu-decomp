extern "C" void func_61370fd0(void *p)
{
    unsigned *head = (unsigned *)p;
    unsigned a = head[0];
    unsigned b;
    if (a != 0) {
        b = head[1];
        *(unsigned *)(a + 4) = b;
    }
    b = head[1];
    if (b != 0) {
        *(unsigned *)b = a;
    }
    head[0] = 0;
    head[1] = 0;
}