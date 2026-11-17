extern "C" {

extern unsigned D_62145a1c;
void *_ZN2nn2os11GetTlsValueENS0_7TlsSlotE(unsigned);

unsigned func_61369d84(void)
{
    unsigned char *p = *(unsigned char **)&D_62145a1c;
    unsigned slot = *(unsigned *)(p + 0x48);
    unsigned char *r = (unsigned char *)_ZN2nn2os11GetTlsValueENS0_7TlsSlotE(slot);
    return *(unsigned *)(r + 0x60);
}

}