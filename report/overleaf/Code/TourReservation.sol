// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TourReservation {
    address public operator;
    uint256 public totalSeats;
    uint256 public availableSeats;
    uint256 public ticketPrice; // Don vi: wei (0.08 ETH = 80000000000000000 wei)
    bool public isTourActive;

    // Luu so ve da dat theo tung dia chi vi
    mapping(address => uint256) private bookings;

    event TourCreated(uint256 totalSeats, uint256 ticketPrice);
    event SeatsBooked(address indexed customer, uint256 seats, uint256 totalPaid);

    modifier onlyOperator() {
        require(msg.sender == operator, "Chi dieu hanh moi co quyen thuc hien");
        _;
    }

    constructor() {
        operator = msg.sender;
    }

    // 1. Chi dieu hanh tao tour voi so cho duong va gia ve duong
    function createTour(uint256 _totalSeats, uint256 _ticketPrice) external onlyOperator {
        require(_totalSeats > 0, "So cho phai lon hon 0");
        require(_ticketPrice > 0, "Gia ve phai lon hon 0");

        totalSeats = _totalSeats;
        availableSeats = _totalSeats;
        ticketPrice = _ticketPrice;
        isTourActive = true;

        emit TourCreated(_totalSeats, _ticketPrice);
    }

    // 2. Khach hang dat cho: nguyen duong, khong vuot cho trong, thanh toan dung phi
    function bookSeats(uint256 _seats) external payable {
        require(isTourActive, "Hien chua co tour nao duoc mo");
        require(_seats > 0, "So cho dat phai lon hon 0");
        require(_seats <= availableSeats, "Khong du cho trong");
        require(msg.value == _seats * ticketPrice, "Thanh toan khong dung phi");

        availableSeats -= _seats;
        bookings[msg.sender] += _seats;

        emit SeatsBooked(msg.sender, _seats, msg.value);
    }

    // 3. Xem so cho trong con lai
    function getAvailableSeats() external view returns (uint256) {
        return availableSeats;
    }

    // 4. Xem so ve da dat cua vi dang goi
    function getMyBookings() external view returns (uint256) {
        return bookings[msg.sender];
    }
}