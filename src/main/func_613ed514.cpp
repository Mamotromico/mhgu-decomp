extern "C" {

struct Data {
    volatile unsigned int field0;
    volatile unsigned int field4;
    volatile unsigned int field8;
    volatile unsigned int field12;
    volatile unsigned char field16;
};

void func_613ed514(Data *d) {
    d->field0 = 0;
    d->field4 = 0;
    d->field8 = 0;
    d->field12 = 0;
    d->field16 = 0;
}

}