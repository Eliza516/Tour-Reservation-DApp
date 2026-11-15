import { useEffect, useState } from "react";
import { CONTRACT_ADDRESS, TOUR_DEFAULT } from "./config/contract";
import {
  connectMetaMaskWallet,
  createWeb3Instance,
  formatShortAddress,
  getNetworkName,
  getTourContract,
  getWalletSnapshot,
  hasMetaMask,
} from "./utils/web3Client";
import "./App.css";

function App() {
  const isOnChainMode = Boolean(CONTRACT_ADDRESS);

  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [balanceEth, setBalanceEth] = useState("0.0000");
  const [chainId, setChainId] = useState(null);

  const [operatorAddress, setOperatorAddress] = useState("");
  const [totalSeats, setTotalSeats] = useState(TOUR_DEFAULT.totalSeats);
  const [availableSeats, setAvailableSeats] = useState(TOUR_DEFAULT.totalSeats);
  const [ticketPriceEth, setTicketPriceEth] = useState(TOUR_DEFAULT.ticketPriceEth);
  const [tourCreated, setTourCreated] = useState(true);

  const [mockBookingsByWallet, setMockBookingsByWallet] = useState({});
  const [myBookings, setMyBookings] = useState(0);

  const [seatsToBook, setSeatsToBook] = useState("1");
  const [newTourSeats, setNewTourSeats] = useState(String(TOUR_DEFAULT.totalSeats));
  const [newTourPrice, setNewTourPrice] = useState(TOUR_DEFAULT.ticketPriceEth);

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const showStatus = (type, text) => setStatusMessage({ type, text });

  const isOperator =
    account &&
    operatorAddress &&
    account.toLowerCase() === operatorAddress.toLowerCase();

  const syncOnChainData = async (web3Instance, activeAccount) => {
    const contract = getTourContract(web3Instance);
    if (!contract) return;

    const [op, priceWei, total, avail, booked] = await Promise.all([
      contract.methods.operator().call(),
      contract.methods.ticketPrice().call(),
      contract.methods.totalSeats().call(),
      contract.methods.getAvailableSeats().call(),
      contract.methods.getMyBookings().call({ from: activeAccount }),
    ]);

    setOperatorAddress(op);
    setTicketPriceEth(web3Instance.utils.fromWei(priceWei, "ether"));
    setTotalSeats(Number(total));
    setAvailableSeats(Number(avail));
    setMyBookings(Number(booked));
    setTourCreated(Number(total) > 0);
  };

  useEffect(() => {
    if (!isOnChainMode && account) {
      setMyBookings(mockBookingsByWallet[account.toLowerCase()] || 0);
    } else if (!account) {
      setMyBookings(0);
    }
  }, [account, isOnChainMode, mockBookingsByWallet]);

  useEffect(() => {
    if (!hasMetaMask()) return;

    const handleAccountsChanged = async (accounts) => {
      if (!accounts || accounts.length === 0) {
        setAccount("");
        setBalanceEth("0.0000");
        setMyBookings(0);
        showStatus("info", "Vi MetaMask da ngat ket noi.");
        return;
      }

      const nextAccount = accounts[0];
      setAccount(nextAccount);

      try {
        const w3 = web3 || createWeb3Instance();
        setWeb3(w3);
        const snapshot = await getWalletSnapshot(w3, nextAccount);
        setBalanceEth(snapshot.balanceEth);
        setChainId(snapshot.chainId);

        if (isOnChainMode) {
          await syncOnChainData(w3, nextAccount);
        }
      } catch (err) {
        showStatus("error", err.message);
      }
    };

    const handleChainChanged = () => window.location.reload();

    window.ethereum.on("accountsChanged", handleAccountsChanged);
    window.ethereum.on("chainChanged", handleChainChanged);

    return () => {
      window.ethereum.removeListener("accountsChanged", handleAccountsChanged);
      window.ethereum.removeListener("chainChanged", handleChainChanged);
    };
  }, [web3, isOnChainMode]);

  const handleConnectWallet = async () => {
    setLoading(true);
    try {
      const { web3: w3, account: acc, balanceEth: bal, chainId: netId } =
        await connectMetaMaskWallet();

      setWeb3(w3);
      setAccount(acc);
      setBalanceEth(bal);
      setChainId(netId);

      if (!isOnChainMode && !operatorAddress) {
        setOperatorAddress(acc);
      }

      if (isOnChainMode) {
        await syncOnChainData(w3, acc);
      }

      showStatus("success", `Da ket noi vi ${formatShortAddress(acc)} thanh cong!`);
    } catch (err) {
      showStatus("error", err.message || "Khong the ket noi MetaMask.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTour = async (e) => {
    e.preventDefault();
    if (!account) return showStatus("error", "Vui long ket noi vi MetaMask truoc.");

    const seatsNum = Number(newTourSeats);
    const priceNum = Number(newTourPrice);

    if (!Number.isInteger(seatsNum) || seatsNum <= 0) {
      return showStatus("error", "So cho cua tour phai la so nguyen duong (> 0).");
    }
    if (Number.isNaN(priceNum) || priceNum <= 0) {
      return showStatus("error", "Gia ve tour phai lon hon 0 ETH.");
    }
    if (!isOperator) {
      return showStatus("error", "Chi vi Dieu hanh (Operator) moi co quyen tao tour.");
    }

    setLoading(true);
    try {
      if (isOnChainMode) {
        const contract = getTourContract(web3);
        const priceWei = web3.utils.toWei(String(newTourPrice), "ether");
        await contract.methods.createTour(seatsNum, priceWei).send({ from: account });
        await syncOnChainData(web3, account);
      } else {
        setTotalSeats(seatsNum);
        setAvailableSeats(seatsNum);
        setTicketPriceEth(String(priceNum));
        setMockBookingsByWallet({});
        setMyBookings(0);
        setTourCreated(true);
      }
      showStatus("success", `Da mo tour moi voi ${seatsNum} cho, gia ${priceNum} ETH/nguoi!`);
    } catch (err) {
      showStatus("error", err.message || "Tao tour that bai.");
    } finally {
      setLoading(false);
    }
  };

  const handleBookSeats = async (e) => {
    e.preventDefault();
    if (!account) return showStatus("error", "Vui long ket noi vi MetaMask truoc khi dat cho.");
    if (!tourCreated) return showStatus("error", "Hien chua co tour nao duoc mo.");

    const seatsNum = Number(seatsToBook);
    if (!Number.isInteger(seatsNum) || seatsNum <= 0) {
      return showStatus("error", "So cho dat phai la so nguyen duong (> 0).");
    }
    if (seatsNum > availableSeats) {
      return showStatus(
        "error",
        `So cho dat (${seatsNum}) vuot qua so cho trong con lai (${availableSeats}).`
      );
    }

    const totalCostEth = (seatsNum * Number(ticketPriceEth)).toFixed(4);

    setLoading(true);
    try {
      if (isOnChainMode) {
        const contract = getTourContract(web3);
        const priceWei = BigInt(web3.utils.toWei(String(ticketPriceEth), "ether"));
        const valueWei = (priceWei * BigInt(seatsNum)).toString();

        await contract.methods.bookSeats(seatsNum).send({
          from: account,
          value: valueWei,
        });

        const snapshot = await getWalletSnapshot(web3, account);
        setBalanceEth(snapshot.balanceEth);
        await syncOnChainData(web3, account);
      } else {
        setAvailableSeats((prev) => prev - seatsNum);
        const key = account.toLowerCase();
        setMockBookingsByWallet((prev) => ({
          ...prev,
          [key]: (prev[key] || 0) + seatsNum,
        }));
      }

      showStatus("success", `Dat thanh cong ${seatsNum} cho (Thanh toan ${totalCostEth} ETH)!`);
    } catch (err) {
      showStatus("error", err.message || "Dat cho that bai.");
    } finally {
      setLoading(false);
    }
  };

  const calculatedTotalEth =
    Number(seatsToBook) > 0 && Number.isInteger(Number(seatsToBook))
      ? (Number(seatsToBook) * Number(ticketPriceEth)).toFixed(4)
      : "0.0000";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-badge">De 36</span>
          <div>
            <h1>Tour Reservation DApp</h1>
            <p className="subtitle">Dat ve du lich minh bach tren Web3 &amp; Solidity</p>
          </div>
        </div>

        <div className="wallet-area">
          {account ? (
            <div className="wallet-pill">
              <span className={`role-tag ${isOperator ? "operator" : "customer"}`}>
                {isOperator ? "Dieu hanh" : "Khach hang"}
              </span>
              <span className="network-tag">{getNetworkName(chainId)}</span>
              <span className="balance-tag">{balanceEth} ETH</span>
              <span className="address-tag" title={account}>
                {formatShortAddress(account)}
              </span>
            </div>
          ) : (
            <button className="btn btn-primary" onClick={handleConnectWallet} disabled={loading}>
              {loading ? "Dang ket noi..." : "Ket noi MetaMask"}
            </button>
          )}
        </div>
      </header>

      <main className="container">
        <div className={`mode-banner ${isOnChainMode ? "onchain" : "mock"}`}>
          {isOnChainMode ? (
            <>
              <strong>Che do On-Chain:</strong> Dang ket noi Smart Contract tai{" "}
              <code>{formatShortAddress(CONTRACT_ADDRESS)}</code>
            </>
          ) : (
            <>
              <strong>Che do mo phong:</strong> Chua co <code>CONTRACT_ADDRESS</code>.
            </>
          )}
        </div>

        {statusMessage && (
          <div className={`alert alert-${statusMessage.type}`}>
            <span>{statusMessage.text}</span>
            <button className="alert-close" onClick={() => setStatusMessage(null)}>
              x
            </button>
          </div>
        )}

        <section className="stats-grid">
          <div className="stat-card">
            <span className="stat-label">Gia ve / nguoi</span>
            <strong className="stat-value">{ticketPriceEth} ETH</strong>
            <span className="stat-hint">Thanh toan dung phi khi dat</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Cho trong con lai</span>
            <strong className="stat-value accent">
              {availableSeats} / {totalSeats}
            </strong>
            <span className="stat-hint">Ham: getAvailableSeats()</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">
              {isOperator ? "So cho da duoc dat" : "Ve ban da dat"}
            </span>
            <strong className="stat-value">
              {isOperator ? `${Math.max(totalSeats - availableSeats, 0)} cho` : `${myBookings} cho`}
            </strong>
            <span className="stat-hint">
              {isOperator ? "Tong hop toan tour" : "Ham: getMyBookings()"}
            </span>
          </div>
        </section>

        <section className="role-panel-wrap">
          {!account ? (
            <div className="panel panel-center">
              <h2>Chua ket noi vi MetaMask</h2>
              <p className="panel-desc">
                Vui long ket noi vi MetaMask. He thong se tu dong nhan dien ban la{" "}
                <strong>Dieu hanh</strong> hay <strong>Khach hang</strong> de hien thi giao
                dien phu hop.
              </p>
              <button className="btn btn-primary" onClick={handleConnectWallet} disabled={loading}>
                {loading ? "Dang ket noi..." : "Ket noi MetaMask ngay"}
              </button>
            </div>
          ) : isOperator ? (
            <div className="panel">
              <div className="panel-header">
                <h2>Giao dien Dieu hanh - Mo / Tao Tour</h2>
                <span className="fn-chip">createTour()</span>
              </div>
              <p className="panel-desc">
                Ban dang dang nhap bang vi Dieu hanh{" "}
                <code>{formatShortAddress(operatorAddress)}</code>.
              </p>

              <form onSubmit={handleCreateTour} className="form-stack">
                <label className="field">
                  <span>Tong so cho (nguyen duong)</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={newTourSeats}
                    onChange={(e) => setNewTourSeats(e.target.value)}
                    required
                  />
                </label>

                <label className="field">
                  <span>Gia ve moi nguoi (ETH)</span>
                  <input
                    type="number"
                    min="0.0001"
                    step="any"
                    value={newTourPrice}
                    onChange={(e) => setNewTourPrice(e.target.value)}
                    required
                  />
                </label>

                <button type="submit" className="btn btn-secondary btn-full" disabled={loading}>
                  {loading ? "Dang xu ly..." : "Tao / Mo lai Tour"}
                </button>
              </form>
            </div>
          ) : (
            <div className="panel">
              <div className="panel-header">
                <h2>Giao dien Khach hang - Dat cho Tour</h2>
                <span className="fn-chip">bookSeats()</span>
              </div>
              <p className="panel-desc">{TOUR_DEFAULT.name}</p>

              <form onSubmit={handleBookSeats} className="form-stack">
                <label className="field">
                  <span>So luong cho muon dat</span>
                  <input
                    type="number"
                    min="1"
                    max={availableSeats || 1}
                    step="1"
                    value={seatsToBook}
                    onChange={(e) => setSeatsToBook(e.target.value)}
                    required
                  />
                </label>

                <div className="summary-row">
                  <span>Tong thanh toan du kien:</span>
                  <strong>{calculatedTotalEth} ETH</strong>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary btn-full"
                  disabled={loading || availableSeats === 0}
                >
                  {availableSeats === 0
                    ? "Tour da het cho"
                    : loading
                    ? "Dang xu ly..."
                    : "Dat cho ngay"}
                </button>
              </form>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;