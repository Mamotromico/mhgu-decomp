extern "C" unsigned int func_61365600(unsigned int* self) {
    unsigned int v = self[-1];
    unsigned int* q = (unsigned int*)(v - 1);
    if ((v & 1) == 0)
        q = self - 4;
    return q[3];
}