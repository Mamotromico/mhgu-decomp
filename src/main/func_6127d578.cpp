extern "C" {

extern char D_6213e03c[];

void _ZN2nn2os11UnlockMutexEPNS0_9MutexTypeE(void *);

void func_6127d578(char *p) {
    if (*(volatile unsigned char *)(D_6213e03c) != 0)
        return;
    _ZN2nn2os11UnlockMutexEPNS0_9MutexTypeE(p + 0xd4);
}

}